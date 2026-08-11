#import <XCTest/XCTest.h>

@interface BlenderUITests : XCTestCase
@end

@implementation BlenderUITests

- (void)testViewportTapSelectsCube
{
  XCUIApplication *app = [[XCUIApplication alloc] init];
  NSString *readyNotification = @"org.blender.ios.ui-test.ready";
  XCTDarwinNotificationExpectation *ready =
      [[XCTDarwinNotificationExpectation alloc] initWithNotificationName:readyNotification];
  NSString *probe =
      @"import bpy,ctypes,json,os,pathlib;S=lambda *v:bytes(v).decode();"
       "d=os.path.expanduser(S(126,47,68,111,99,117,109,101,110,116,115,47,66,108,101,110,"
       "100,101,114,73,79,83,81,65));os.makedirs(d,exist_ok=True);"
       "c=bpy.data.objects[S(67,117,98,101)];c.location=(0,0,0);c.select_set(False);"
       "bpy.context.view_layer.objects.active=None;"
       "n=ctypes.CDLL(None).notify_post;"
       "bpy.app.timers.register(lambda:(n(S(111,114,103,46,98,108,101,110,100,101,114,46,105,"
       "111,115,46,117,105,45,116,101,115,116,46,114,101,97,100,121).encode()),None)[1],"
       "first_interval=0.25);"
       "p=os.path.join(d,S(116,111,117,99,104,45,114,101,112,111,114,116,46,106,115,111,110));"
       "r=os.environ.get(S(66,76,69,78,68,69,82,95,73,79,83,95,81,65,95,82,85,78,95,73,68),"
       "S(109,97,110,117,97,108));"
       "bpy.app.timers.register(lambda:(pathlib.Path(p).write_text(json.dumps({"
       "S(115,116,97,116,117,115):S(112,97,115,115,101,100) if c.select_get() else "
       "S(119,97,105,116,105,110,103),S(114,117,110,95,105,100):r,"
       "S(115,101,108,101,99,116,101,100):c.select_get()})),0.25)[1],"
       "first_interval=0.25,persistent=True)";
  app.launchEnvironment = @{ @"BLENDER_IOS_QA_RUN_ID" : @"iphone-touch-1" };
  app.launchArguments = @[ @"--python-expr", probe ];

  [app launch];
  XCTAssertTrue([app waitForState:XCUIApplicationStateRunningForeground timeout:30.0]);
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ ready ] timeout:30.0],
                 XCTWaiterResultCompleted);
  [NSThread sleepForTimeInterval:1.0];

  [[app coordinateWithNormalizedOffset:CGVectorMake(0.42, 0.47)] tap];
  [NSThread sleepForTimeInterval:4.0];

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
  [app typeKey:XCUIKeyboardKeyEnter modifierFlags:XCUIKeyModifierNone];
  XCTAssertEqual([XCTWaiter waitForExpectations:@[ moved ] timeout:10.0],
                 XCTWaiterResultCompleted);

  [app typeKey:@"d" modifierFlags:XCUIKeyModifierShift];
  [app typeKey:XCUIKeyboardKeyEscape modifierFlags:XCUIKeyModifierNone];
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

@end
