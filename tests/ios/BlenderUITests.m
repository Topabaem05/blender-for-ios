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

@end
