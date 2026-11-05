#import "PQEventsStore.h"

static NSString *const kKey = @"puzzlequest.events";

@implementation PQEventsStore

+ (instancetype)sharedStore
{
    static PQEventsStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQEventsStore alloc] init];
    });
    return shared;
}

- (NSInteger)activeCount
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setActiveCount:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
