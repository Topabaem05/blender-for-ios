#import <XCTest/XCTest.h>

@interface BlenderUITests : XCTestCase
@end

@implementation BlenderUITests

- (void)setUp
{
  [super setUp];
  XCUIDevice.sharedDevice.orientation = UIDeviceOrientationLandscapeLeft;
}

- (void)testViewportTapSelectsCube
{
  XCUIApplication *app = [[XCUIApplication alloc] init];
  NSString *readyNotification = @"org.blender.ios.ui-test.ready";
  NSString *selectedNotification = @"org.blender.ios.ui-test.selected";
  XCTDarwinNotificationExpectation *ready =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:readyNotification];
  XCTDarwinNotificationExpectation *selected = [[XCTDarwinNotificationExpectation alloc]
      initWithNotificationName:selectedNotification];
  NSString *probe =
      @"import bpy,ctypes,json,os,pathlib;S=lambda *v:bytes(v).decode();"
       "d=os.path.expanduser(S(126,47,68,111,99,117,109,101,110,116,115,47,66,108,101,110,"
       "100,101,114,73,79,83,81,65));os.makedirs(d,exist_ok=True);"
       "c=bpy.data.objects[S(67,117,98,101)];c.location=(0,0,0);c.select_set(False);"
       "bpy.context.view_layer.objects.active=None;"
       "n=ctypes.CDLL(None).notify_post;"
       "V=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,117,105,45,116,101,"
       "115,116,46,115,101,108,101,99,116,101,100).encode();s=[0];"
       "bpy.app.timers.register(lambda:(n(S(111,114,103,46,98,108,101,110,100,101,114,46,105,"
       "111,115,46,117,105,45,116,101,115,116,46,114,101,97,100,121).encode()),None)[1],"
       "first_interval=0.25);"
       "p=os.path.join(d,S(116,111,117,99,104,45,114,101,112,111,114,116,46,106,115,111,110));"
       "r=os.environ.get(S(66,76,69,78,68,69,82,95,73,79,83,95,81,65,95,82,85,78,95,73,68),"
       "S(109,97,110,117,97,108));"
       "bpy.app.timers.register(lambda:(pathlib.Path(p).write_text(json.dumps({"
       "S(115,116,97,116,117,115):S(112,97,115,115,101,100) if c.select_get() else "
       "S(119,97,105,116,105,110,103),S(114,117,110,95,105,100):r,"
       "S(115,101,108,101,99,116,101,100):c.select_get()})),"
       "(n(V),s.__setitem__(0,1)) if c.select_get() and s[0]==0 else 0,.25)[2],"
       "first_interval=0.25,persistent=True)";
  app.launchEnvironment = @{ @"BLENDER_IOS_QA_RUN_ID" : @"iphone-touch-1" };
  app.launchArguments = @[ @"--python-expr", probe ];

  [app launch];
  XCTAssertTrue([app waitForState:XCUIApplicationStateRunningForeground timeout:30.0]);
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ ready ] timeout:30.0],
                 XCTWaiterResultCompleted);

  [[app coordinateWithNormalizedOffset:CGVectorMake(0.42, 0.47)] tap];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ selected ] timeout:10.0],
                 XCTWaiterResultCompleted);

  XCTAttachment *attachment = [XCTAttachment attachmentWithScreenshot:[app screenshot]];
  attachment.name = @"Blender after viewport tap";
  attachment.lifetime = XCTAttachmentLifetimeKeepAlways;
  [self addAttachment:attachment];
  XCTAssertEqual(app.state, XCUIApplicationStateRunningForeground);
}

- (void)testAppleKeyboardShortcutsReachBlender
{
  XCUIApplication *app = [[XCUIApplication alloc] init];
  NSString *readyName = @"org.blender.ios.keyboard.ready";
  NSString *movedName = @"org.blender.ios.keyboard.moved";
  NSString *shiftName = @"org.blender.ios.keyboard.shift";
  NSString *optionName = @"org.blender.ios.keyboard.option";
  NSString *commandName = @"org.blender.ios.keyboard.command";
  NSString *controlName = @"org.blender.ios.keyboard.control";
  XCTDarwinNotificationExpectation *ready =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:readyName];
  XCTDarwinNotificationExpectation *moved =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:movedName];
  XCTDarwinNotificationExpectation *shifted =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:shiftName];
  XCTDarwinNotificationExpectation *optioned =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:optionName];
  XCTDarwinNotificationExpectation *commanded =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:commandName];
  XCTDarwinNotificationExpectation *controlled =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:controlName];
  NSString *probe =
      @"import bpy,ctypes;S=lambda *v:bytes(v).decode();"
       "c=bpy.data.objects[S(67,117,98,101)];"
       "[bpy.data.objects.remove(o,do_unlink=True) for o in list(bpy.data.objects) if o!=c and "
       "o.name.startswith(S(67,117,98,101))];"
       "[o.select_set(False) for o in bpy.context.selected_objects];"
       "c.location=(0,0,0);c.select_set(True);bpy.context.view_layer.objects.active=c;"
       "n=ctypes.CDLL(None).notify_post;"
       "R=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,107,101,121,98,111,"
       "97,114,100,46,114,101,97,100,121).encode();"
       "M=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,107,101,121,98,111,"
       "97,114,100,46,109,111,118,101,100).encode();"
       "H=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,107,101,121,98,111,"
       "97,114,100,46,115,104,105,102,116).encode();"
       "O=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,107,101,121,98,111,"
       "97,114,100,46,111,112,116,105,111,110).encode();"
       "D=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,107,101,121,98,111,"
       "97,114,100,46,99,111,109,109,97,110,100).encode();"
       "T=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,107,101,121,98,111,"
       "97,114,100,46,99,111,110,116,114,111,108).encode();"
       "s=[0];q=lambda:[o for o in bpy.data.objects if o.name.startswith(S(67,117,98,101))];"
       "a=lambda:bpy.context.view_layer.objects.active;"
       "f=lambda:((n(M),s.__setitem__(0,1),.1)[2] if s[0]==0 and abs(c.location.x-1)<.001 else "
       "(n(H),s.__setitem__(0,2),.1)[2] if s[0]==1 and len(q())>1 else "
       "(n(O),s.__setitem__(0,3),.1)[2] if s[0]==2 and a() and abs(a().location.x)<.001 else "
       "(n(D),s.__setitem__(0,4),.1)[2] if s[0]==3 and a() and abs(a().location.x-1)<.001 else "
       "(n(T),s.__setitem__(0,5),None)[2] if s[0]==4 and "
       "bpy.context.screen.show_fullscreen else .1);"
       "bpy.app.timers.register(f,first_interval=.1,persistent=True);"
       "bpy.app.timers.register(lambda:(n(R),None)[1],first_interval=.25)";
  app.launchArguments = @[ @"--python-expr", probe ];

  [app launch];
  XCTAssertTrue([app waitForState:XCUIApplicationStateRunningForeground timeout:30.0]);
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ ready ] timeout:30.0],
                 XCTWaiterResultCompleted);
  [[app coordinateWithNormalizedOffset:CGVectorMake(0.42, 0.47)] tap];

  [app typeKey:@"g" modifierFlags:XCUIKeyModifierNone];
  [app typeKey:@"x" modifierFlags:XCUIKeyModifierNone];
  [app typeKey:@"1" modifierFlags:XCUIKeyModifierNone];
  /* XCTest misroutes Enter and drops Escape on iOS; Space is a native transform confirm key. */
  [app typeKey:XCUIKeyboardKeySpace modifierFlags:XCUIKeyModifierNone];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ moved ] timeout:10.0],
                 XCTWaiterResultCompleted);

  [app typeKey:@"d" modifierFlags:XCUIKeyModifierShift];
  [app typeKey:XCUIKeyboardKeySpace modifierFlags:XCUIKeyModifierNone];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ shifted ] timeout:10.0],
                 XCTWaiterResultCompleted);

  [app typeKey:@"g" modifierFlags:XCUIKeyModifierOption];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ optioned ] timeout:10.0],
                 XCTWaiterResultCompleted);

  [app typeKey:@"z" modifierFlags:XCUIKeyModifierCommand];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ commanded ] timeout:10.0],
                 XCTWaiterResultCompleted);

  [app typeKey:XCUIKeyboardKeySpace modifierFlags:XCUIKeyModifierControl];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ controlled ] timeout:10.0],
                 XCTWaiterResultCompleted);

  XCTAttachment *attachment = [XCTAttachment attachmentWithScreenshot:[app screenshot]];
  attachment.name = @"Blender after Apple keyboard shortcuts";
  attachment.lifetime = XCTAttachmentLifetimeKeepAlways;
  [self addAttachment:attachment];
  XCTAssertEqual(app.state, XCUIApplicationStateRunningForeground);
}

- (void)testSoftwareKeyboardCommitsTextToBlender
{
  XCUIApplication *app = [[XCUIApplication alloc] init];
  NSString *readyName = @"org.blender.ios.software-keyboard.ready";
  NSString *completedName = @"org.blender.ios.software-keyboard.completed";
  XCTDarwinNotificationExpectation *ready = [[XCTDarwinNotificationExpectation alloc]
      initWithNotificationName:readyName];
  XCTDarwinNotificationExpectation *completed = [[XCTDarwinNotificationExpectation alloc]
      initWithNotificationName:completedName];
  NSString *probe =
      @"import bpy,ctypes;S=lambda *v:bytes(v).decode();"
       "n=ctypes.CDLL(None).notify_post;"
       "K=S(105,111,115,95,115,111,102,116,119,97,114,101,95,107,101,121,98,111,97,114,"
       "100,95,112,114,111,98,101);"
       "N=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,115,111,102,116,"
       "119,97,114,101,45,107,101,121,98,111,97,114,100,46,99,111,109,112,108,101,116,"
       "101,100).encode();"
       "R=S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,115,111,102,116,"
       "119,97,114,101,45,107,101,121,98,111,97,114,100,46,114,101,97,100,121).encode();"
       "E=S(73,79,83,32,83,111,102,116,119,97,114,101,32,75,101,121,98,111,97,114,100,"
       "32,80,114,111,98,101);"
       "u=lambda s,c:(c.scene.__setitem__(K,s.value),n(N) if s.value==E else 0,None)[2];"
       "f=lambda s,c:{S(70,73,78,73,83,72,69,68)};"
       "i=lambda s,c,e:(c.window.cursor_warp(c.window.width//2,c.window.height//2),"
       "c.window_manager.invoke_props_dialog(s),"
       "bpy.app.timers.register(lambda:(n(R),None)[1],first_interval=.5))[1];"
       "P=type(S(73,79,83,95,79,84,95,115,111,102,116,119,97,114,101,95,107,101,121,98,"
       "111,97,114,100,95,112,114,111,98,101),(bpy.types.Operator,),{"
       "S(98,108,95,105,100,110,97,109,101):S(119,109,46,105,111,115,95,115,111,102,116,"
       "119,97,114,101,95,107,101,121,98,111,97,114,100,95,112,114,111,98,101),"
       "S(98,108,95,108,97,98,101,108):S(73,79,83,32,83,111,102,116,119,97,114,101,32,"
       "75,101,121,98,111,97,114,100,32,80,114,111,98,101),"
       "S(95,95,97,110,110,111,116,97,116,105,111,110,115,95,95):{"
       "S(118,97,108,117,101):bpy.props.StringProperty(name=S(84,101,120,116),update=u)},"
       "S(105,110,118,111,107,101):i,"
       "S(101,120,101,99,117,116,101):f});"
       "bpy.utils.register_class(P);"
       "bpy.app.timers.register(lambda:(bpy.ops.wm.ios_software_keyboard_probe("
       "S(73,78,86,79,75,69,95,68,69,70,65,85,76,84)),None)[1],first_interval=1.0)";
  app.launchArguments = @[ @"--python-expr", probe ];

  [app launch];
  XCTAssertTrue([app waitForState:XCUIApplicationStateRunningForeground timeout:30.0]);
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ ready ] timeout:60.0],
                 XCTWaiterResultCompleted);

  [[app coordinateWithNormalizedOffset:CGVectorMake(0.51, 0.47)] tap];

  XCUIElement *textField = app.textFields.firstMatch;
  XCTAssertTrue([textField waitForExistenceWithTimeout:15.0]);
  [textField tap];
  [textField typeText:@"IOS Software Keyboard Probe한"];
  [textField typeKey:XCUIKeyboardKeyDelete modifierFlags:XCUIKeyModifierNone];

  NSPredicate *enabled = [NSPredicate predicateWithFormat:@"enabled == YES"];
  XCUIElement *doneButton = [[app.toolbars.buttons matchingPredicate:enabled]
      elementBoundByIndex:0];
  XCTAssertTrue([doneButton waitForExistenceWithTimeout:10.0]);
  [doneButton tap];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ completed ] timeout:10.0],
                 XCTWaiterResultCompleted);

  XCTAttachment *attachment = [XCTAttachment attachmentWithScreenshot:[app screenshot]];
  attachment.name = @"Blender after software keyboard text commit";
  attachment.lifetime = XCTAttachmentLifetimeKeepAlways;
  [self addAttachment:attachment];
  XCTAssertEqual(app.state, XCUIApplicationStateRunningForeground);
}

- (void)testEditorSurvivesPortraitAndLandscapeRotation
{
  XCUIApplication *app = [[XCUIApplication alloc] init];
  NSString *readyName = @"org.blender.ios.rotation.ready";
  XCTDarwinNotificationExpectation *ready = [[XCTDarwinNotificationExpectation alloc]
      initWithNotificationName:readyName];
  NSString *probe =
      @"import bpy,ctypes;S=lambda *v:bytes(v).decode();"
       "bpy.app.timers.register(lambda:(ctypes.CDLL(None).notify_post("
       "S(111,114,103,46,98,108,101,110,100,101,114,46,105,111,115,46,114,111,116,97,"
       "116,105,111,110,46,114,101,97,100,121).encode()),None)[1],first_interval=.25)";
  app.launchArguments = @[ @"--python-expr", probe ];
  [app launch];
  XCTAssertTrue([app waitForState:XCUIApplicationStateRunningForeground timeout:30.0]);
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ ready ] timeout:90.0],
                 XCTWaiterResultCompleted);
  XCUIElement *window = app.windows.firstMatch;
  XCTAssertTrue([window waitForExistenceWithTimeout:10.0]);

  XCUIDevice.sharedDevice.orientation = UIDeviceOrientationPortrait;
  NSPredicate *portraitFramePredicate = [NSPredicate
      predicateWithBlock:^BOOL(id evaluatedObject, NSDictionary<NSString *, id> *bindings) {
        (void)evaluatedObject;
        (void)bindings;
        CGRect frame = window.frame;
        return frame.size.height > frame.size.width;
      }];
  XCTNSPredicateExpectation *portraitFrame = [[XCTNSPredicateExpectation alloc]
      initWithPredicate:portraitFramePredicate
                 object:window];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ portraitFrame ] timeout:10.0],
                 XCTWaiterResultCompleted);
  XCTAssertEqual(XCUIDevice.sharedDevice.orientation, UIDeviceOrientationPortrait);
  XCTAssertEqual(app.state, XCUIApplicationStateRunningForeground);

  XCTAttachment *portrait = [XCTAttachment attachmentWithScreenshot:[app screenshot]];
  portrait.name = @"Blender editor in portrait";
  portrait.lifetime = XCTAttachmentLifetimeKeepAlways;
  [self addAttachment:portrait];

  XCUIDevice.sharedDevice.orientation = UIDeviceOrientationLandscapeRight;
  NSPredicate *landscapeFramePredicate = [NSPredicate
      predicateWithBlock:^BOOL(id evaluatedObject, NSDictionary<NSString *, id> *bindings) {
        (void)evaluatedObject;
        (void)bindings;
        CGRect frame = window.frame;
        return frame.size.width > frame.size.height;
      }];
  XCTNSPredicateExpectation *landscapeFrame = [[XCTNSPredicateExpectation alloc]
      initWithPredicate:landscapeFramePredicate
                 object:window];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ landscapeFrame ] timeout:10.0],
                 XCTWaiterResultCompleted);
  XCTAssertEqual(XCUIDevice.sharedDevice.orientation, UIDeviceOrientationLandscapeRight);
  XCTAssertEqual(app.state, XCUIApplicationStateRunningForeground);

  XCTAttachment *landscape = [XCTAttachment attachmentWithScreenshot:[app screenshot]];
  landscape.name = @"Blender editor after rotation to landscape";
  landscape.lifetime = XCTAttachmentLifetimeKeepAlways;
  [self addAttachment:landscape];
}

@end
